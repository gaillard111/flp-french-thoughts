<?php

namespace Application\Sonata\UserBundle\Controller;

use Application\Sonata\UserBundle\Entity\Friendship;
use Application\Sonata\UserBundle\Entity\User;
use Application\Sonata\UserBundle\Form\Type\ThoughtType;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\RequestStack;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;
use Symfony\Component\Routing\RouteCompiler;
use ThoughtBundle\Entity\Author;
use ThoughtBundle\Entity\Thought;
use ThoughtBundle\Model\AuthorModel;
use ThoughtBundle\Service\Mail;

/**
 * Class ThoughtController
 * @package Application\Sonata\UserBundle\Controller
 */
class ThoughtController extends Controller
{
    /**
     * @param $routeName
     * @return Response
     * @throws \Doctrine\ORM\Query\QueryException
     */
    public function menuAction($routeName)
    {
        $menu = [];

        $menu[] = [
            'label' => 'Tableau de bord',
            'route' => 'fos_user_profile_show',
        ];

        $menu[] = [
            'label' => 'Profil',
            'route' => 'fos_user_profile_edit',
        ];

        $menu[] = [
            'label' => 'My profile',
            'route' => 'thought_profile',
            'parameters' => [
                'userId' => $this->getUser()->getId(),
            ]
        ];

        $menu[] = [
            'label' => 'My friends',
            'route' => 'friends',
        ];

        /** @var User $user */
        $user = $this->getUser();

        $menu[] = [
            'label' => $this->get('translator')->trans('user.dialogs.title'),
            'route' => 'dialog_list',
        ];

        $menu[] = [
            'label' => 'Insérer une citation',
            'route' => 'sonata_user_thought_create',
        ];

        $menu[] = [
            'label' => 'Mes citations',
            'route' => 'sonata_user_thoughts',
        ];

        $menu[] = [
            'label' => 'Mes chaines',
            'route' => 'sonata_user_chains',
        ];

        $menu[] = [
            'label' => 'Mes chaînes préférées',
            'route' => 'sonata_user_favorite_chains',
        ];

        $menu[] = [
            'label' => 'Chaines partagées',
            'route' => 'sonata_user_shared_chains',
        ];

        $thoughts = $this->container
            ->get('thought.model.thought_model')->getCountUserThoughts($this->getUser());

        /** @var RequestStack $requestStack */
        $requestStack = $this->get('request_stack');


        return $this->render('@ApplicationSonataUser/Profile/menu.html.twig', [
            'menu'          => $menu,
            'routeName'     => $routeName,
            'thoughts'      => $thoughts,
            'dialogsCount'  => $user->getDialogs()->count(),
            'userProfileId' => $requestStack->getMasterRequest()->get('userId')
        ]);
    }

    /**
     * @Route("/thoughts", name="sonata_user_thoughts")
     * @param Request $request
     * @return Response
     */
    public function listAction(Request $request)
    {
        $thoughts = $this->container
            ->get('thought.model.thought_model')
            ->getUserThoughts($this->getUser())
            ->getResult();
//        $paginator  = $this->get('knp_paginator');
//        $pagination = $paginator->paginate(
//            $thoughts,
//            $request->query->getInt('page', 1)
//        );
        return $this->render('ApplicationSonataUserBundle:Thought:list.html.twig', array(
            'thoughts' => $thoughts,
        ));
    }

    /**
     * @Route("/thought/create", name="sonata_user_thought_create")
     * @param Request $request
     * @return \Symfony\Component\HttpFoundation\RedirectResponse|Response
     * @throws \Exception
     */
    public function createAction(Request $request)
    {
        $thought = new Thought();
        $em = $this->getDoctrine()->getManager();

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
        return $this->render('ApplicationSonataUserBundle:Thought:create.html.twig', array(
            'form' => $form->createView(),
        ));
    }

    /**
     * @Route("/thought/autocomplete/author", name="sonata_user_thought_autocomplete_author")
     *
     * @param Request $request
     * @return Response
     */
    public function autocompleteThoughtAuthorAction(Request $request) {

        $nameStartsWith = $request->get('nameStartsWith');

        /** @var AuthorModel $authorModel */
        $authorModel = $this->container->get('thought.model.author_model');

        $authors = $authorModel->getAuthorsByStringStart($nameStartsWith);

        $data = array();
        /** @var Author $author */
        foreach($authors as $author){
            $authorData = array();

            $authorData["name"]      = $author->getName();
            $authorData["birthDate"] = $author->getBirthDate();
            $authorData["sex"]       = $author->getSex();
            $authorData["country"]   = $author->getCountry();
            $authorData["continent"] = $author->getContinent();
            $authorData["job"]       = $author->getJob();

            $data[] = $authorData;
        }

        return new JsonResponse($data);
    }
}
