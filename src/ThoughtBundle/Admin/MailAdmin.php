<?php
/**
 * Created by PhpStorm.
 * User: ars
 * Date: 03.08.18
 * Time: 12:50
 */

namespace ThoughtBundle\Admin;

use Doctrine\ORM\EntityManagerInterface;
use Doctrine\ORM\Event\LifecycleEventArgs;
use Sonata\AdminBundle\Admin\Admin;
use Sonata\AdminBundle\Form\FormMapper;
use Sonata\AdminBundle\Datagrid\DatagridMapper;
use Sonata\AdminBundle\Datagrid\ListMapper;
use Sonata\AdminBundle\Route\RouteCollection;
use ThoughtBundle\Entity\GeneralMail;

class MailAdmin extends Admin
{
    private $rootPath;



    /**
     * @param FormMapper $formMapper
     */
    protected function configureFormFields(FormMapper $formMapper)
    {
        $formMapper
            ->add('subject')
            ->add('body', 'textarea', [
                'label' => 'Message',
                'attr'  => [
                    'class' => 'js-ckeditor'
                ],
            ]);
    }

    /**
     * @param ListMapper $listMapper
     */
    protected function configureListFields(ListMapper $listMapper)
    {
        $listMapper
            ->addIdentifier('id')
//            ->add('mailTo')
            ->add('subject')
            ->add('body')
            ->add('isSended');
    }

    /**
     * @param DatagridMapper $datagridMapper
     */
    protected function configureDatagridFilters(DatagridMapper $datagridMapper)
    {
        foreach ($this->getFilterFields() as $filterField) {
            $datagridMapper->add($filterField);
        }
    }

    /**
     * @return array
     */
    public function getFilterFields()
    {
        return array(
//            'mailTo',
            'subject',
            'body',
            'isSended'
        );
    }

    public function setMyRootPath($rootPath)
    {
        $this->rootPath = $rootPath;
    }

    public function postPersist($object)
    {
        $this->sendEmailForAllUsers($object);
    }

    public function postUpdate($object)
    {
        $this->sendEmailForAllUsers($object);
    }

    private function sendEmailForAllUsers($object)
    {
        $root = $this->rootPath;
        /** @var GeneralMail $object */
        $mailId  = $object->getId();
        $command = '/usr/bin/php7.0 ' . $root . '/console throught:mail_command ' . $mailId . ' > /dev/null 2>&1 &';

//        dump($command); die;

        exec($command);
    }
}