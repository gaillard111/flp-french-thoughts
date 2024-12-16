<?php

namespace ThoughtBundle\Controller\Profile;

use Application\Sonata\UserBundle\Entity\Message;
use Application\Sonata\UserBundle\Entity\User;
use Application\Sonata\UserBundle\Form\Object\SearchObject;
use Application\Sonata\UserBundle\Form\Type\SortSearchForm;
use Application\Sonata\UserBundle\Form\Type\ThoughtType;
use Doctrine\ORM\NonUniqueResultException;
use Doctrine\ORM\OptimisticLockException;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\ParamConverter;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;
use ThoughtBundle\Entity\Author;
use ThoughtBundle\Entity\Thought;
use ThoughtBundle\Model\AuthorModel;
use ThoughtBundle\Service\Mail;

/**
 * @Route("/profile")
 */
class ThoughtController extends Controller
{
    /**
     * @Route("/thoughts", name="profile_thoughts_list")
     * @Route("/student/{user_id}/thoughts", name="student_thoughts")
     * @ParamConverter("student", options={"mapping"={"user_id"="id"}})
     * @param Request $request
     * @return Response
     */
    public function listAction(Request $request, User $student = null)
    {
        $user = $this->getUser();

        if (!is_null($student)) {
            $this->denyAccessUnlessGranted($student, $this->getUser());
            $user = $student;
        }

        $searchObject = new SearchObject();
        $form         = $this->createForm(new SortSearchForm(), $searchObject);
        $form->handleRequest($request);

        $search = '';
        if ($searchObject->getSearchString()) {
            $search = $searchObject->getSearchString();
        }

        $thoughts = $this->container
            ->get('thought.model.thought_model')
            ->getUserThoughts($user, $searchObject->getSort(), $search)
            ->getResult();
        $paginator  = $this->get('knp_paginator');
        $pagination = $paginator->paginate(
            $thoughts,
            $request->query->getInt('page', 1)
        );

        return $this->render('ThoughtBundle:Profile/Thoughts:list.html.twig', [
            'thoughts' => $pagination,
            'form'     => $form->createView(),
            'student' => $student,
        ]);
    }

    /**
     * @Route("/thought/create", name="sonata_user_thought_create")
     * @param Request $request
     * @return RedirectResponse|Response
     * @throws \Exception
     */
    public function createAction(Request $request)
    {
        $thought = new Thought();
        $em      = $this->getDoctrine()->getManager();

        $form = $this->createForm(new ThoughtType(), $thought);
        $form->handleRequest($request);
        $author = new Author();
        if ($request->getMethod() == 'POST') {
//            if ($form->isValid()) {
                /** @var AuthorModel $authorModel */
                $authorModel = $this->container->get('thought.model.author_model');

                $authorName = $thought->getAuthor();

                if (!$authorModel->findAuthorByName($authorName)) {
                    $authorData = $request->get('sonata_user_author_create');

                    $author->setName($authorName);
                    $author->setSex($authorData['sex']);
                    $author->setJob($authorData['job']);
                    $author->setContinent($authorData['continent']);
                    $author->setBirthDate($authorData['birthDate']);
                    $author->setCountry($authorData['country']);

                    $em->persist($author);
                }

                $thought->setOwner($this->getUser());
                $em->persist($thought);
                $em->flush();

                /** @var Mail $serviceMail */
                $serviceMail = $this->container->get('thought.service.mail_service');
                $serviceMail->mailAddNewThought($thought);

                return $this->redirect($this->generateUrl('profile_thoughts_list'));
            }
//        }
        return $this->render('ThoughtBundle:Profile/Thoughts:create.html.twig', [
            'form'   => $form->createView(),
            'author' => $author,
        ]);
    }

    /**
     * @Route("/thought/{id}/edit", name="sonata_user_thought_edit", requirements={"id"="\d+"})
     * @Route("/student/{user_id}/thought/{id}/edit", name="student_thought_edit")
     * @ParamConverter("student", options={"mapping"={"user_id"="id"}})
     * @throws OptimisticLockException
     * @param Request $request
     * @param User $student
     * @param $id
     * @return Response
     */
    public function updateAction(Request $request, $id, User $student = null)
    {
        $user = $this->getUser();

        if (!is_null($student)) {
            $this->denyAccessUnlessGranted($student, $this->getUser());
            $user = $student;
            $teacher = true;
        }

        $em = $this->get('doctrine.orm.entity_manager');
        /** @var Thought $thought */
        $thought = $em->getRepository(Thought::class)->find($id);
        $author  = $em->getRepository(Author::class)->findOneBy([
            'name' => $thought->getAuthor(),
        ]);

        if (!$thought) {
            return $this->redirectToRoute('thought_homepage_index');
        }

        if (($thought->getOwner() != $this->getUser()) && !$this->isGranted('ROLE_MODERATOR') && !$teacher) {
            return $this->redirectToRoute('thought_homepage_index');
        }

        $form = $this->createForm(new ThoughtType(), $thought);
        $form->handleRequest($request);

        $em->persist($thought);
        $em->flush();

        return $this->render('ThoughtBundle:Profile/Thoughts:create.html.twig', [
            'form'   => $form->createView(),
            'author' => $author,
            'student' => $student
        ]);
    }

    /**
     * @Route("/thought/autocomplete/author", name="sonata_user_thought_autocomplete_author")
     * @param Request $request
     * @return Response
     */
    public function autocompleteThoughtAuthorAction(Request $request)
    {
        $nameStartsWith = $request->get('nameStartsWith');

        /** @var AuthorModel $authorModel */
        $authorModel = $this->container->get('thought.model.author_model');

        $authors = $authorModel->getAuthorsByStringStart($nameStartsWith);

        $data = [];
        /** @var Author $author */
        foreach ($authors as $author) {
            $authorData = [];

            $authorData['name']      = $author->getName();
            $authorData['birthDate'] = $author->getBirthDate();
            $authorData['sex']       = $author->getSex();
            $authorData['country']   = $author->getCountry();
            $authorData['continent'] = $author->getContinent();
            $authorData['job']       = $author->getJob();

            $data[] = $authorData;
        }

        return new JsonResponse($data);
    }

    /**
     * @Route("/thought/{thought_id}/publish", name="thought_publish")
     * @ParamConverter("thought", options={"mapping"={"thought_id"="id"}})
     * @param Request $request
     * @return Response
     */
    public function publishThought(Thought $thought) {
        $this->denyAccessUnlessGranted($thought->getOwner(), $this->getUser());
        $em = $this->getDoctrine()->getManager();
        if ($thought->isPublish()) {
            $thought->setPublished(false);
        } else {
            $thought->setPublished(true);
        }
        $em->persist($thought);
        $em->flush();
        return $this->redirectToRoute('student_thoughts', ['user_id' => $thought->getOwner()->getId()]);
    }
}
