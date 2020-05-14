<?php

namespace Application\Sonata\UserBundle\Controller;

use Application\Sonata\UserBundle\Entity\Message;
use Application\Sonata\UserBundle\Entity\User;
use Application\Sonata\UserBundle\Form\Object\SearchObject;
use Application\Sonata\UserBundle\Form\Type\SortSearchForm;
use Application\Sonata\UserBundle\Form\Type\ThoughtType;
use Doctrine\ORM\NonUniqueResultException;
use Doctrine\ORM\OptimisticLockException;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\RequestStack;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpFoundation\StreamedResponse;
use Symfony\Component\Routing\Annotation\Route;
use ThoughtBundle\Entity\Author;
use ThoughtBundle\Entity\MenuItem;
use ThoughtBundle\Entity\Thought;
use ThoughtBundle\Entity\Topic;
use ThoughtBundle\Model\AuthorModel;
use ThoughtBundle\Service\Mail;

/**
 * Class ThoughtController
 *
 * @package Application\Sonata\UserBundle\Controller
 */
class ThoughtController extends Controller
{
    public function navbarAction()
    {
        $roots = $this->getDoctrine()->getRepository(MenuItem::class)->findBy(['level' => 0], ['sort' => 'ASC']);

        $virtualRoot = new MenuItem();
        $virtualRoot->setChildren($roots);

        return $this->render('@Thought/navigate.html.twig', [
            'root' => $virtualRoot,
        ]);
    }

    /**
     * @param $routeName
     *
     * @return Response
     *
     * @throws NonUniqueResultException
     * @throws \Doctrine\ORM\Query\QueryException
     */
    public function menuAction($routeName, $mobile = false)
    {
        $menuService = $this->get('thought.menu');
        $menu        = $menuService->makeMenu($this->getUser());

        /** @var User $user */
        $user = $this->getUser();

        $thoughts = $this->container
            ->get('thought.model.thought_model')->getCountUserThoughts($this->getUser());

        /** @var RequestStack $requestStack */
        $requestStack = $this->get('request_stack');

        $count       = $this->getDoctrine()->getRepository(Message::class)->getCountNewMessages($user);
        $countTopics = $this->getDoctrine()->getRepository(Topic::class)->getCountUserTopics($user);
        if (!$mobile) {
            return $this->render('@ApplicationSonataUser/Profile/menu.html.twig', [
                'menu'             => $menu,
                'routeName'        => $routeName,
                'thoughts'         => $thoughts,
                'newMessagesCount' => $count,
                'countTopics'      => $countTopics,
                'userProfileId'    => $requestStack->getMasterRequest()->get('userId'),
            ]);
        } else {
            return $this->render('@ApplicationSonataUser/Profile/mobile_menu.html.twig', [
                'menu'             => $menu,
                'routeName'        => $routeName,
                'thoughts'         => $thoughts,
                'newMessagesCount' => $count,
                'countTopics'      => $countTopics,
                'userProfileId'    => $requestStack->getMasterRequest()->get('userId'),
            ]);
        }
    }

    /**
     * @Route("/ajax-counter", name="ajax_counter")
     *
     * @return JsonResponse
     *
     * @throws NonUniqueResultException
     */
    public function ajaxCounter()
    {
        $messages = $this->getDoctrine()->getRepository(Message::class)->getCountNewMessages($this->getUser());
        return new JsonResponse([
            'count' => $messages,
        ]);
    }

    /**
     * @Route("/most-favorite/add/{thoughtId}", name="add_to_most_favorites")
     *
     * @param int $thoughtId
     *
     * @return JsonResponse
     *
     * @throws OptimisticLockException
     */
    public function ajaxAddToMostFavorites($thoughtId)
    {
        $em = $this->get('doctrine.orm.entity_manager');
        /** @var Thought $thought */
        $thought = $em->getRepository(Thought::class)->find($thoughtId);
        /** @var User $user */
        $user = $this->getUser();

        $userThoughts = $user->getMostFavoriteThoughts();

        if ($userThoughts->contains($thought)) {
            return new JsonResponse(['result' => 'already exists'], 400);
        }
        $user->addThoughtToMostFavorite($thought);
        $em->persist($user);
        $em->flush();
        return new JsonResponse(['result' => 'success'], 200);
    }

    /**
     * @Route("/most-favorite/delete/{thoughtId}", name="delete_from_most_favorites")
     *
     * @param $thoughtId
     *
     * @return JsonResponse
     *
     * @throws OptimisticLockException
     */
    public function ajaxDeleteFromMostFavorites($thoughtId)
    {
        $em = $this->get('doctrine.orm.entity_manager');
        /** @var Thought $thought */
        $thought = $em->getRepository(Thought::class)->find($thoughtId);
        /** @var User $user */
        $user = $this->getUser();

        $userThoughts = $user->getMostFavoriteThoughts();

        if (!$userThoughts->contains($thought)) {
            return new JsonResponse(['result' => 'Not found'], 404);
        }
//        dump($thought); die;
        $user->deleteThoughtFromMostFavorites($thought);
        $em->persist($user);
        $em->flush();
        return new JsonResponse(['result' => 'success'], 200);
    }

    /**
     * @Route("/favorite", name="favorite-quotes")
     */
    public function favoriteQuotesAction()
    {
        $likedThoughts = $this->getDoctrine()->getRepository(Thought::class)->getLikedThoughts($this->getUser());

        return $this->render('ApplicationSonataUserBundle:Thought:favorite_list.html.twig', [
            'thoughts' => $likedThoughts,
        ]);
    }

    /**
     * @Route("favorite/export", name="export-favorite-quotes")
     */
    public function exportFavoriteToCsvAction()
    {
        $likedThoughts = $this->getDoctrine()->getRepository(Thought::class)->getLikedThoughts($this->getUser());
        $response      = new StreamedResponse();

        $response->setCallback(function () use ($likedThoughts) {
            $handle = fopen('php://output', 'w+');

            fputcsv($handle, ['Citation', 'Auteur', 'Catégorie', 'Created'], ',');

            /** @var Thought[] $likedThoughts */
            foreach ($likedThoughts as $thought) {
                fputcsv($handle, [$thought->getContent(), $thought->getAuthor(), $thought->getCategory(), $thought->getCreatedAt()->format('d.m.Y H:i')], ',');
            }

            fclose($handle);
        });

        $response->setStatusCode(200);
        $response->headers->set('Content-Type', 'text/csv; charset=utf-8');
        $response->headers->set('Content-Disposition', 'attachment; filename="export.csv"');
        return $response;
    }

    /**
     * @Route("/thoughts", name="sonata_user_thoughts")
     *
     * @param Request $request
     *
     * @return Response
     */
    public function listAction(Request $request)
    {
        $searchObject = new SearchObject();
        $form         = $this->createForm(new SortSearchForm(), $searchObject);
        $form->handleRequest($request);

        $search = '';
        if ($searchObject->getSearchString()) {
            $search = $searchObject->getSearchString();
        }

        $thoughts = $this->container
            ->get('thought.model.thought_model')
            ->getUserThoughts($this->getUser(), $searchObject->getSort(), $search)
            ->getResult();
//        $paginator  = $this->get('knp_paginator');
//        $pagination = $paginator->paginate(
//            $thoughts,
//            $request->query->getInt('page', 1)
//        );
        return $this->render('ApplicationSonataUserBundle:Thought:list.html.twig', [
            'thoughts' => $thoughts,
            'form'     => $form->createView(),
        ]);
    }

    /**
     * @Route("/thought/create", name="sonata_user_thought_create")
     *
     * @param Request $request
     *
     * @return RedirectResponse|Response
     *
     * @throws \Exception
     */
    public function createAction(Request $request)
    {
        $thought = new Thought();
        $em      = $this->getDoctrine()->getManager();

        $form = $this->createForm(new ThoughtType(), $thought);
        $form->handleRequest($request);
        if ($request->getMethod() == 'POST') {
            if ($form->isValid()) {
                /** @var AuthorModel $authorModel */
                $authorModel = $this->container->get('thought.model.author_model');

                $authorName = $thought->getAuthor();

                if (!$authorModel->findAuthorByName($authorName)) {
                    $authorData = $request->get('sonata_user_author_create');

                    $author = new Author();

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

                return $this->redirect($this->generateUrl('sonata_user_thoughts'));
            }
        }
        return $this->render('ApplicationSonataUserBundle:Thought:create.html.twig', [
            'form' => $form->createView(),
        ]);
    }

    /**
     * @param Request $request
     * @param $id
     *
     * @return Response
     *
     * @throws OptimisticLockException
     * @Route("/thought/{id}/edit", name="sonata_user_thought_edit", requirements={"id"="\d+"})
     */
    public function updateAction(Request $request, $id)
    {
        $em = $this->get('doctrine.orm.entity_manager');
        /** @var Thought $thought */
        $thought = $em->getRepository(Thought::class)->find($id);

        if (!$thought) {
            return $this->redirectToRoute('thought_homepage_index');
        }

        if (($thought->getOwner() != $this->getUser()) && !$this->isGranted('ROLE_MODERATOR')) {
            return $this->redirectToRoute('thought_homepage_index');
        }

        $form = $this->createForm(new ThoughtType(), $thought);
        $form->handleRequest($request);

        if ($form->isValid()) {
            $thought->setOwner($this->getUser());

            $em->persist($thought);
            $em->flush();
        }

        return $this->render('ApplicationSonataUserBundle:Thought:create.html.twig', [
            'form' => $form->createView(),
        ]);
    }

    /**
     * @Route("/thought/autocomplete/author", name="sonata_user_thought_autocomplete_author")
     *
     * @param Request $request
     *
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
}
