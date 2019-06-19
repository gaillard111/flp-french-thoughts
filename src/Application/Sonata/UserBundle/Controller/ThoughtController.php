<?php

namespace Application\Sonata\UserBundle\Controller;

use Application\Sonata\UserBundle\Entity\Message;
use Application\Sonata\UserBundle\Entity\User;
use Application\Sonata\UserBundle\Form\Object\SearchObject;
use Application\Sonata\UserBundle\Form\Type\SortSearchForm;
use Application\Sonata\UserBundle\Form\Type\ThoughtType;
use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\RequestStack;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Annotation\Route;
use ThoughtBundle\Entity\Author;
use ThoughtBundle\Entity\Thought;
use ThoughtBundle\Entity\Topic;
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
     * @throws \Doctrine\ORM\NonUniqueResultException
     * @throws \Doctrine\ORM\Query\QueryException
     */
    public function menuAction($routeName)
    {
        $menu = [];

        $menu[] = [
            'label' => $this->get('translator')->trans('navbar.profile'),
            'route' => 'fos_user_profile_edit',
        ];

        $menu[] = [
            'label' => $this->get('translator')->trans('user.form.profile.profile_edit'),
            'route' => 'thought_profile',
            'parameters' => [
                'userId' => $this->getUser()->getId(),
            ]
        ];
        $menu[] = [
            'label' => $this->get('translator')->trans('user.friendship.title'),
            'route' => 'friends',
        ];

        /** @var User $user */
        $user = $this->getUser();

        $menu[] = [
            'label' => $this->get('translator')->trans('user.dialogs.title'),
            'route' => 'dialog_list',
        ];

        $menu[] = [
            'label' => $this->get('translator')->trans('user.thought.create_page.title'),
            'route' => 'sonata_user_thought_create',
        ];

        $menu[] = [
            'label' => $this->get('translator')->trans('user.thought.list_page.title'),
            'route' => 'sonata_user_thoughts',
        ];

        $menu[] = [
            'label' => $this->get('translator')->trans('thought.menu.favorite_thoughts'),
            'route' => 'favorite-quotes',
        ];

        $menu[] = [
            'label' => $this->get('translator')->trans('user.topic.list_page.title'),
            'route' => 'sonata_user_topics',
        ];

        $menu[] = [
            'label' => $this->get('translator')->trans('user.chain.list_page.title'),
            'route' => 'sonata_user_chains',
        ];

        $thoughts = $this->container
            ->get('thought.model.thought_model')->getCountUserThoughts($this->getUser());

        /** @var RequestStack $requestStack */
        $requestStack = $this->get('request_stack');

        $count          = $this->getDoctrine()->getRepository(Message::class)->getCountNewMessages($user);
        $countTopics    = $this->getDoctrine()->getRepository(Topic::class)->getCountUserTopics($user);

        return $this->render('@ApplicationSonataUser/Profile/menu.html.twig', [
            'menu'             => $menu,
            'routeName'        => $routeName,
            'thoughts'         => $thoughts,
            'newMessagesCount' => $count,
            'countTopics'      => $countTopics,
            'userProfileId'    => $requestStack->getMasterRequest()->get('userId')
        ]);
    }

    /**
     * @Route("/ajax-counter", name="ajax_counter")
     * @return JsonResponse
     * @throws \Doctrine\ORM\NonUniqueResultException
     */
    public function ajaxCounter()
    {
        $messages = $this->getDoctrine()->getRepository(Message::class)->getCountNewMessages($this->getUser());
        return new JsonResponse([
            'count' =>  $messages
        ]);
    }

    /**
     * @Route("/favorite", name="favorite-quotes")
     */
    public function favoriteQuotesAction()
    {
        $user = $this->getUser();
        $likedThoughts = $this->getDoctrine()->getRepository(Thought::class)->getLikedThoughts($this->getUser());

        return $this->render('ApplicationSonataUserBundle:Thought:favorite_list.html.twig', [
            'thoughts'  => $likedThoughts
        ]);
    }

    /**
     * @Route("/thoughts", name="sonata_user_thoughts")
     * @param Request $request
     * @return Response
     */
    public function listAction(Request $request)
    {
        $searchObject = new SearchObject();
        $form = $this->createForm(new SortSearchForm(), $searchObject);
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
        dump($form->getData());
        return $this->render('ApplicationSonataUserBundle:Thought:list.html.twig', array(
            'thoughts' => $thoughts,
            'form'     => $form->createView()
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
